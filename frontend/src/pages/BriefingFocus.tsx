import { Navigate, useParams } from "react-router-dom";
import { keyFromSlug } from "../briefings/keys";
import DeadLawSection from "../briefings/DeadLawSection";
import Ley30Section from "../briefings/Ley30Section";
import OmnibusSection from "../briefings/OmnibusSection";
import UnreadableSection from "../briefings/UnreadableSection";

const SECTIONS = {
  "unreadable-laws": UnreadableSection,
  "omnibus-laws": OmnibusSection,
  "dead-law-dependencies": DeadLawSection,
  "ley-30-1992-blast-radius": Ley30Section,
} as const;

export default function BriefingFocus() {
  const { slug } = useParams<{ slug: string }>();
  const key = slug ? keyFromSlug(slug) : null;
  if (!key) return <Navigate to="/" replace />;
  const Section = SECTIONS[key];
  return (
    <div className="briefing-focus">
      <Section focusMode />
    </div>
  );
}
