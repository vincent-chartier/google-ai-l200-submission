resource "google_logging_metric" "dlp_redactions" {
  project     = var.project_id
  name        = "${var.app_name}-${var.environment}-dlp-redactions"
  description = "Count of sensitive PII detections and Cloud DLP sanitizations in Cinema Outings logs"
  filter      = "resource.type=\"cloud_run_revision\" AND (jsonPayload.cloud_dlp.is_sensitive=true OR textPayload=~\"\\[REDACTED_\")"

  metric_descriptor {
    metric_kind  = "DELTA"
    value_type   = "INT64"
    unit         = "1"
    display_name = "Cloud DLP Redactions Count"
  }
}

resource "google_monitoring_alert_policy" "high_5xx_errors" {
  count        = var.enable_alerts ? 1 : 0
  project      = var.project_id
  display_name = "${var.app_name}-${var.environment}-high-5xx-error-rate"
  combiner     = "OR"

  conditions {
    display_name = "Cloud Run 5xx Error Rate > ${var.error_rate_threshold} req/sec"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.cloud_run_service_name}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.error_rate_threshold

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.labels.service_name"]
      }
    }
  }
}

resource "google_monitoring_dashboard" "multi_agent_dashboard" {
  project = var.project_id
  dashboard_json = jsonencode({
    displayName = "Cinema Outings Multi-Agent Observability (${upper(var.environment)})"
    gridLayout = {
      columns = "2"
      widgets = [
        {
          title = "Agent Request Count by Status"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${var.cloud_run_service_name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                      groupByFields      = ["metric.labels.response_code_class"]
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Request Latency Percentiles (p50, p95, p99)"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${var.cloud_run_service_name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_PERCENTILE_99"
                      crossSeriesReducer = "REDUCE_NONE"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Container CPU Utilization"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/container/cpu/utilizations\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${var.cloud_run_service_name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_PERCENTILE_95"
                      crossSeriesReducer = "REDUCE_NONE"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Container Memory Utilization"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/container/memory/utilizations\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${var.cloud_run_service_name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_PERCENTILE_95"
                      crossSeriesReducer = "REDUCE_NONE"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Active Instance Count"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/container/instance_count\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${var.cloud_run_service_name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_MEAN"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Cloud DLP Sensitive Data Redactions Count"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.dlp_redactions.name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_DELTA"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
              }
            ]
          }
        }
      ]
    }
  })
}
