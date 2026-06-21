export interface InsightCard {
  anchor: string;
  title: string;
  mainNumber: string;
  subtitle: string;
  actionLabel: string;
}

export interface OverviewInsights {
  cards: InsightCard[];
}
