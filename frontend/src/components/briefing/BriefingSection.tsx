import type { ReactNode } from "react";

interface Props {
  id: string;
  children: ReactNode;
}

export default function BriefingSection({ id, children }: Props) {
  return (
    <section id={id} className="briefing-section">
      {children}
    </section>
  );
}
