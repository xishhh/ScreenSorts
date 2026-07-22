export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center">
      <div className="flex flex-col items-center gap-6 text-center">
        <h1 className="text-4xl font-bold tracking-tight">ScreenSorts</h1>
        <p className="text-lg text-muted-foreground max-w-md">
          AI-Powered Semantic Screenshot Search Engine
        </p>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          Frontend is running
        </div>
      </div>
    </div>
  );
}
