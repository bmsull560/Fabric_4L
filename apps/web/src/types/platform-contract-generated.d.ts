declare module '@fabric/platform-contract/generated' {
  export namespace layer1_ingestion {
    export interface components {
      schemas: {
        JobSummary: Record<string, unknown>;
        ComplianceSummaryResponse: Record<string, unknown>;
      };
    }
  }

  export namespace layer2_extraction {
    export interface components {
      schemas: {
        ExtractionStatusResponse: Record<string, unknown>;
      };
    }
  }

  export namespace layer4_agents {
    export interface components {
      schemas: {
        BusinessCaseResponse: Record<string, unknown>;
      };
    }
  }
}
