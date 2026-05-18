/**
 * Deliverable route helpers — canonical §2.6 route construction for deliverables.
 *
 * All deliverable URL strings must be built here, not inline in page components.
 * Uses getStatePath() from navigationService so route definitions stay in one place.
 */
import { getStatePath } from "@/navigation/navigationService";

export const deliverableRoutes = {
  /** /deliverables/cases/:caseId */
  businessCaseDetail: (caseId: string): string =>
    getStatePath("business-case-detail", { caseId }),

  /** /deliverables/cases */
  businessCaseList: (): string =>
    getStatePath("business-cases"),
};
