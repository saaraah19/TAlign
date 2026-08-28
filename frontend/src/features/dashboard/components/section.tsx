export function Section({
  title,
  empty,
  children,
}: {
  title: string;
  empty: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h2 className="mb-2 text-sm font-medium text-gray-900">{title}</h2>
      {empty ? <p className="text-sm text-gray-500">Nothing here right now.</p> : children}
    </div>
  );
}
