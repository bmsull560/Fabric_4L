export interface ApiEntityResultDto {
  id?: string;
  entity_id?: string;
  name?: string;
  title?: string;
  entity_type?: string;
  type?: string;
  confidence_score?: number;
  confidence?: number;
  description?: string;
  properties?: Record<string, unknown>;
  data?: Record<string, unknown>;
}

export interface ApiIngestionJobDto {
  id?: string;
  status?: string;
  created_at?: string;
  started_at?: string;
  updated_at?: string;
  progress_percent_complete?: number;
  progress_processed_pages?: number;
  configuration?: {
    url?: string;
  };
}

export interface ApiIngestionAggregationDto {
  by_status?: Record<string, number>;
  total_records_extracted?: number;
  total_execution_time_ms?: number;
}

export interface ApiWorkflowStepDto {
  agent?: string;
  result?: {
    output?: unknown;
  };
}

export interface ApiBusinessCaseUseCaseDto {
  name?: string;
  persona?: string;
  value_driver?: string;
  roi_value?: number;
  payback_months?: number;
  confidence?: number;
}

export interface ApiBusinessCaseRoiOutputDto {
  use_cases?: ApiBusinessCaseUseCaseDto[];
  total_value?: number;
  avg_payback_months?: number;
  confidence?: number;
}

export interface ApiBusinessCaseNarrativeOutputDto {
  executive_summary?: string;
}

export interface ApiWorkflowResultDto {
  output?: {
    company_name?: string;
  };
  steps?: ApiWorkflowStepDto[];
  completed_at?: string;
}

export interface ApiProgressLogDto {
  timestamp?: string;
  level?: string;
  message?: string;
  status?: string;
}

export interface ApiExtractedEntityDto {
  type?: string;
  name?: string;
}

export interface ApiExtractionJobDto {
  id?: string;
  status?: string;
  progress_percent_complete?: number;
  progress_pages_found?: number;
  progress_processed_pages?: number;
  progress_logs?: ApiProgressLogDto[];
  extracted_entities?: ApiExtractedEntityDto[];
  created_at?: string;
  updated_at?: string;
  configuration?: {
    url?: string;
  };
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null;

const asString = (value: unknown): string | undefined =>
  typeof value === 'string' ? value : undefined;

const asNumber = (value: unknown): number | undefined =>
  typeof value === 'number' && Number.isFinite(value) ? value : undefined;

const asStringRecord = (value: unknown): Record<string, unknown> | undefined =>
  isRecord(value) ? value : undefined;

const asArray = (value: unknown): unknown[] => (Array.isArray(value) ? value : []);

export const parseEntityResults = (value: unknown): ApiEntityResultDto[] =>
  asArray(value)
    .filter(isRecord)
    .map((item): ApiEntityResultDto => ({
      id: asString(item.id),
      entity_id: asString(item.entity_id),
      name: asString(item.name),
      title: asString(item.title),
      entity_type: asString(item.entity_type),
      type: asString(item.type),
      confidence_score: asNumber(item.confidence_score),
      confidence: asNumber(item.confidence),
      description: asString(item.description),
      properties: asStringRecord(item.properties),
      data: asStringRecord(item.data),
    }));

export const parseIngestionJobs = (value: unknown): ApiIngestionJobDto[] =>
  asArray(value)
    .filter(isRecord)
    .map((item): ApiIngestionJobDto => ({
      id: asString(item.id),
      status: asString(item.status),
      created_at: asString(item.created_at),
      started_at: asString(item.started_at),
      updated_at: asString(item.updated_at),
      progress_percent_complete: asNumber(item.progress_percent_complete),
      progress_processed_pages: asNumber(item.progress_processed_pages),
      configuration: isRecord(item.configuration) ? { url: asString(item.configuration.url) } : undefined,
    }));

export const parseIngestionAggregation = (value: unknown): ApiIngestionAggregationDto => {
  if (!isRecord(value)) return {};
  const byStatusRaw = isRecord(value.by_status) ? value.by_status : undefined;
  const by_status = byStatusRaw
    ? Object.fromEntries(
        Object.entries(byStatusRaw).filter((entry): entry is [string, number] => typeof entry[1] === 'number'),
      )
    : undefined;

  return {
    by_status,
    total_records_extracted: asNumber(value.total_records_extracted),
    total_execution_time_ms: asNumber(value.total_execution_time_ms),
  };
};

export const parseWorkflowResult = (value: unknown): ApiWorkflowResultDto => {
  if (!isRecord(value)) return {};
  const output = isRecord(value.output) ? { company_name: asString(value.output.company_name) } : undefined;
  const steps = asArray(value.steps).filter(isRecord).map((step): ApiWorkflowStepDto => ({
    agent: asString(step.agent),
    result: isRecord(step.result) ? { output: step.result.output } : undefined,
  }));

  return {
    output,
    steps,
    completed_at: asString(value.completed_at),
  };
};

export const parseBusinessCaseRoiOutput = (value: unknown): ApiBusinessCaseRoiOutputDto => {
  if (!isRecord(value)) return {};
  const use_cases = asArray(value.use_cases).filter(isRecord).map((useCase): ApiBusinessCaseUseCaseDto => ({
    name: asString(useCase.name),
    persona: asString(useCase.persona),
    value_driver: asString(useCase.value_driver),
    roi_value: asNumber(useCase.roi_value),
    payback_months: asNumber(useCase.payback_months),
    confidence: asNumber(useCase.confidence),
  }));
  return {
    use_cases,
    total_value: asNumber(value.total_value),
    avg_payback_months: asNumber(value.avg_payback_months),
    confidence: asNumber(value.confidence),
  };
};

export const parseBusinessCaseNarrativeOutput = (value: unknown): ApiBusinessCaseNarrativeOutputDto =>
  isRecord(value) ? { executive_summary: asString(value.executive_summary) } : {};

export const parseExtractionJob = (value: unknown): ApiExtractionJobDto => {
  if (!isRecord(value)) return {};
  return {
    id: asString(value.id),
    status: asString(value.status),
    progress_percent_complete: asNumber(value.progress_percent_complete),
    progress_pages_found: asNumber(value.progress_pages_found),
    progress_processed_pages: asNumber(value.progress_processed_pages),
    progress_logs: asArray(value.progress_logs).filter(isRecord).map((log): ApiProgressLogDto => ({
      timestamp: asString(log.timestamp),
      level: asString(log.level),
      message: asString(log.message),
      status: asString(log.status),
    })),
    extracted_entities: asArray(value.extracted_entities).filter(isRecord).map((entity): ApiExtractedEntityDto => ({
      type: asString(entity.type),
      name: asString(entity.name),
    })),
    created_at: asString(value.created_at),
    updated_at: asString(value.updated_at),
    configuration: isRecord(value.configuration) ? { url: asString(value.configuration.url) } : undefined,
  };
};
