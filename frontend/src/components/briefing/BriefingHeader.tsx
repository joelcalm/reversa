import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Maximize2 } from "lucide-react";
import { EvidenceButton } from "../common";
import type { BriefingKey } from "../../types";
import { BRIEFING_ROUTE_SLUG } from "../../briefings/keys";

interface Props {
  number: number;
  title: string;
  question: string;
  headline: ReactNode;
  answer: string;
  scopeNote?: string;
  onViewEvidence?: () => void;
  primaryAction?: ReactNode;
  briefingKey: BriefingKey;
  focusMode?: boolean;
  children?: ReactNode;
}

export default function BriefingHeader({
  number,
  title,
  question,
  headline,
  answer,
  scopeNote,
  onViewEvidence,
  primaryAction,
  briefingKey,
  focusMode,
  children,
}: Props) {
  const slug = BRIEFING_ROUTE_SLUG[briefingKey];
  return (
    <header className="briefing-header">
      <div className="briefing-header-top">
        <span className="briefing-number">Briefing {number}</span>
        {scopeNote && <span className="scope-note">{scopeNote}</span>}
      </div>
      <h2 className="briefing-title">{title}</h2>
      <p className="briefing-question">{question}</p>
      <div className="briefing-answer-row">
        <div className="briefing-headline">{headline}</div>
        <p className="briefing-interpret">{answer}</p>
      </div>
      <div className="briefing-actions">
        {onViewEvidence && (
          <EvidenceButton onClick={onViewEvidence} />
        )}
        {primaryAction}
        {!focusMode && (
          <Link to={`/briefing/${slug}`} className="btn secondary">
            <Maximize2 size={16} /> Focus this briefing
          </Link>
        )}
        {focusMode && (
          <Link to="/" className="btn secondary">
            Back to Briefing Room
          </Link>
        )}
      </div>
      {children}
    </header>
  );
}
