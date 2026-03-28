const EmptyState = ({
  icon,
  message,
}: {
  icon: React.ReactNode;
  message: string;
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-40 rounded-3xl border-2 border-dashed border-border/20 bg-muted/10 backdrop-blur-sm transition-all hover:bg-muted/20">
      <div className="animate-bounce-slow">{icon}</div>
      <p className="text-muted-foreground italic text-sm font-bold tracking-tight px-12 text-center leading-relaxed">
        {message}
      </p>
      <div className="mt-8 px-6 py-2 rounded-full border border-border/50 bg-background/50 text-[10px] font-black text-muted-foreground/40 uppercase tracking-[0.5em] shadow-inner">
        Awaiting Next Stream
      </div>
    </div>
  );
};

export default EmptyState;
