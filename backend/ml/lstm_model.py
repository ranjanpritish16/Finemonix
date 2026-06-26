import os
import pickle
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from datetime import timedelta
from typing import Optional, Tuple
from sklearn.preprocessing import StandardScaler

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "models")


class CashFlowLSTM(nn.Module):
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        output_horizon: int = 90,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout1 = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, output_horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        out = out[:, -1, :]      # last time-step hidden state
        out = self.dropout1(out)
        out = self.fc(out)
        return out

    def enable_mc_dropout(self) -> None:
        """
        MC Dropout: keep whole model in eval mode but re-enable Dropout layers
        so they actually drop units during inference, giving uncertainty estimates.
        """
        self.eval()
        for module in self.modules():
            if isinstance(module, nn.Dropout):
                module.train()


class CashFlowDataset(Dataset):
    def __init__(
        self,
        X: np.ndarray,
        y: np.ndarray,
        window_size: int = 60,
        horizon: int = 90,
    ):
        self.X = X
        self.y = y
        self.window_size = window_size
        self.horizon = horizon
        self._len = max(0, len(X) - window_size - horizon + 1)

    def __len__(self) -> int:
        return self._len

    def __getitem__(self, idx: int):
        x_window = self.X[idx : idx + self.window_size]
        # Target: the horizon net_cash_flow values immediately after the window
        y_horizon = self.y[idx + self.window_size : idx + self.window_size + self.horizon]
        return (
            torch.tensor(x_window, dtype=torch.float32),
            torch.tensor(y_horizon, dtype=torch.float32),
        )


def train_lstm_model(
    df: pd.DataFrame,
    feature_cols: list,
    target_col: str,
    business_id: int,
    window_size: int = 60,
    horizon: int = 90,
    on_epoch_end: Optional[callable] = None, 
) -> Tuple["CashFlowLSTM", StandardScaler, StandardScaler]:
    """
    Train a 2-layer LSTM to predict net_cash_flow (daily delta).

    TARGET: net_cash_flow — a small value (e.g. +₹5,000 or -₹3,000).
    This is far easier to learn than absolute balance (₹12,00,000).
    forecast.py converts predictions back to running balance via cumsum.

    - target_col must NOT appear in feature_cols (data leakage guard).
    - Scalers fit on FULL dataset before train/val split.
    - Saves weights + scalers to MODEL_DIR.
    """
    # ── Guard: target must not be in features ────────────────────────────────
    if target_col in feature_cols:
        raise ValueError(
            f"target_col '{target_col}' must not appear in feature_cols. "
            "Remove it to prevent data leakage."
        )

    print(f"DEBUG train_lstm_model: {len(df)} rows, "
          f"{len(feature_cols)} features, target={target_col}")
    print(f"DEBUG target stats: mean={df[target_col].mean():,.2f}, "
          f"std={df[target_col].std():,.2f}, "
          f"min={df[target_col].min():,.2f}, "
          f"max={df[target_col].max():,.2f}")

    # ── Adapt window/horizon for small datasets ───────────────────────────────
    # We must ensure: window_size + horizon <= 0.8 * len(df) - 1
    # (because the training set is only 80% of the data)
    train_n = int(len(df) * 0.8)
    max_wh  = train_n - 1   # need at least 1 training sample

    if window_size + horizon > max_wh:
        # Scale down proportionally keeping the ratio
        total = window_size + horizon
        window_size = max(5, int(max_wh * window_size / total))
        horizon     = max(7, max_wh - window_size)
        print(f"DEBUG adapted window={window_size}, horizon={horizon} for small dataset (train_n={train_n})")

    if train_n < window_size + horizon + 1:
        raise ValueError(
            f"Dataset has only {len(df)} rows — too short to train even "
            f"with reduced window={window_size}, horizon={horizon}. "
            "Use the Prophet cold-start model."
        )


    # ── Normalise on FULL dataset before splitting ────────────────────────────
    # net_cash_flow values are small (±₹25k range), so StandardScaler
    # will map them to roughly ±2 — ideal for LSTM training.
    feature_scaler = StandardScaler()
    target_scaler = StandardScaler()

    X_scaled = feature_scaler.fit_transform(df[feature_cols].values).astype(np.float32)
    y_scaled = (
        target_scaler.fit_transform(df[[target_col]].values).flatten().astype(np.float32)
    )

    print(f"DEBUG target_scaler: mean={target_scaler.mean_[0]:,.2f}, "
          f"scale={target_scaler.scale_[0]:,.2f}")

    # ── Train / val split (80 / 20) ───────────────────────────────────────────
    split = int(len(X_scaled) * 0.8)
    X_train, y_train = X_scaled[:split], y_scaled[:split]
    X_val, y_val = X_scaled[split:], y_scaled[split:]

    train_ds = CashFlowDataset(X_train, y_train, window_size, horizon)
    val_ds = CashFlowDataset(X_val, y_val, window_size, horizon)
    has_val = len(val_ds) > 0

    if len(train_ds) == 0:
        raise ValueError("Training dataset is empty after windowing. Provide more data.")

    print(f"DEBUG train_ds={len(train_ds)} samples, val_ds={len(val_ds)} samples")

    train_loader = DataLoader(
        train_ds, batch_size=min(32, max(1, len(train_ds))), shuffle=True
    )
    val_loader = (
        DataLoader(val_ds, batch_size=min(32, max(1, len(val_ds))), shuffle=False)
        if has_val
        else None
    )

    # ── Model ─────────────────────────────────────────────────────────────────
    model = CashFlowLSTM(input_size=len(feature_cols), output_horizon=horizon)
    criterion = nn.HuberLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", patience=5, factor=0.5
    )

    epochs, patience = 100, 10
    best_val_loss = float("inf")
    patience_counter = 0

    for epoch in range(epochs):
        # Training pass
        model.train()
        train_loss = 0.0
        for X_b, y_b in train_loader:
            optimizer.zero_grad()
            pred = model(X_b)
            loss = criterion(pred, y_b)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item() * X_b.size(0)
        train_loss /= len(train_loader.dataset)

        # Validation pass
        if has_val:
            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for X_b, y_b in val_loader:
                    pred = model(X_b)
                    val_loss += criterion(pred, y_b).item() * X_b.size(0)
            val_loss /= len(val_loader.dataset)
        else:
            val_loss = train_loss

        scheduler.step(val_loss)
        if on_epoch_end is not None:
            on_epoch_end(epoch + 1, epochs, val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            os.makedirs(MODEL_DIR, exist_ok=True)
            torch.save(
                model.state_dict(),
                os.path.join(MODEL_DIR, f"lstm_b{business_id}.pt"),
            )
            with open(
                os.path.join(MODEL_DIR, f"lstm_scaler_b{business_id}.pkl"), "wb"
            ) as f:
                pickle.dump(
                    {
                        "feature": feature_scaler,
                        "target": target_scaler,
                        "window": window_size,
                        "horizon": horizon,
                        "feature_cols": feature_cols,
                        "target_col": target_col,
                    },
                    f,
                )
        else:
            patience_counter += 1

        if patience_counter >= patience:
            print(f"DEBUG early stopping at epoch {epoch+1}, best_val_loss={best_val_loss:.6f}")
            break

    print(f"DEBUG training complete. best_val_loss={best_val_loss:.6f}")
    return model, feature_scaler, target_scaler


def predict_lstm_mc_dropout(
    model: "CashFlowLSTM",
    last_window_features: np.ndarray,   # shape (window_size, num_features) — RAW unscaled
    feature_scaler: StandardScaler,
    target_scaler: StandardScaler,
    num_passes: int = 30,
) -> pd.DataFrame:
    """
    MC Dropout inference. Returns predicted NET CASH FLOW per day
    (not running balance). forecast.py converts to running balance via cumsum.

    Returns columns: date, predicted_net, p10_net, p90_net
    """
    model.enable_mc_dropout()

    X_scaled = feature_scaler.transform(last_window_features).astype(np.float32)
    x = torch.tensor(X_scaled, dtype=torch.float32).unsqueeze(0)  # (1, W, F)

    preds: list[np.ndarray] = []
    with torch.no_grad():
        for _ in range(num_passes):
            pred_scaled = model(x).squeeze(0).numpy()              # (horizon,)
            pred_orig = target_scaler.inverse_transform(
                pred_scaled.reshape(-1, 1)
            ).flatten()
            preds.append(pred_orig)

    preds_arr = np.array(preds)                                    # (passes, horizon)
    mean_pred = np.mean(preds_arr, axis=0)
    p10_pred  = np.percentile(preds_arr, 10, axis=0)
    p90_pred  = np.percentile(preds_arr, 90, axis=0)
    cum_preds_arr = np.cumsum(preds_arr, axis=1)                    # (passes, horizon)
    cum_p10_pred  = np.percentile(cum_preds_arr, 10, axis=0)
    cum_p90_pred  = np.percentile(cum_preds_arr, 90, axis=0)
    print(f"DEBUG MC dropout: mean_net day1={mean_pred[0]:,.2f}, "
          f"p10={p10_pred[0]:,.2f}, p90={p90_pred[0]:,.2f}")

    horizon = mean_pred.shape[0]
    base_date = pd.Timestamp.today().date()
    dates = [base_date + timedelta(days=i) for i in range(1, horizon + 1)]

    return pd.DataFrame(
        {
            "date": dates,
            "predicted_net": mean_pred,   # daily net cash flow delta
            "p10_net": p10_pred,
            "p90_net": p90_pred,
            "cum_p10_net": cum_p10_pred,
            "cum_p90_net": cum_p90_pred,
        }
    )


def load_lstm_model(
    business_id: int, input_size: Optional[int] = None
) -> Tuple[Optional["CashFlowLSTM"], Optional[StandardScaler], Optional[StandardScaler]]:
    """
    Load saved model + scalers. Returns (None, None, None) if no checkpoint exists.
    """
    weights_path = os.path.join(MODEL_DIR, f"lstm_b{business_id}.pt")
    scaler_path  = os.path.join(MODEL_DIR, f"lstm_scaler_b{business_id}.pkl")

    if not os.path.exists(weights_path) or not os.path.exists(scaler_path):
        return None, None, None

    with open(scaler_path, "rb") as f:
        meta = pickle.load(f)

    n_features = input_size or len(meta.get("feature_cols", []))
    if n_features == 0:
        raise ValueError(
            "Cannot determine input_size. Pass it explicitly or retrain the model."
        )

    model = CashFlowLSTM(input_size=n_features, output_horizon=meta["horizon"])
    model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    print(f"DEBUG loaded model: features={meta.get('feature_cols')}, "
          f"target={meta.get('target_col')}, horizon={meta['horizon']}")

    return model, meta["feature"], meta["target"]