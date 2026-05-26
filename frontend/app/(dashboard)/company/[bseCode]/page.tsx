export default async function CompanyPage({
  params,
}: {
  params: Promise<{ bseCode: string }>;
}) {
  const { bseCode } = await params;

  return <div style={{ padding: "24px" }}>Company {bseCode}</div>;
}
