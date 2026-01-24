{
  "Comment": "AI Video Generation Pipeline State Machine",
  "StartAt": "Analyze",
  "States": {
    "Analyze": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${agent_lambda_arn}",
        "Payload": {
          "task": "analyze",
          "user_id.$": "$.user_id",
          "job_id.$": "$.job_id",
          "product.$": "$.product",
          "adjustments.$": "$.adjustments"
        }
      },
      "ResultPath": "$.analyze_result",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "FailState"
        }
      ],
      "TimeoutSeconds": 900,
      "Next": "MarketInsight"
    },
    "MarketInsight": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${agent_lambda_arn}",
        "Payload": {
          "task": "market_insight",
          "user_id.$": "$.user_id",
          "job_id.$": "$.job_id",
          "product.$": "$.product",
          "adjustments.$": "$.adjustments",
          "context": {
            "analyze": {
              "output.$": "$.analyze_result.Payload.output"
            }
          }
        }
      },
      "ResultPath": "$.market_insight_result",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "FailState"
        }
      ],
      "TimeoutSeconds": 900,
      "Next": "Generate"
    },
    "Generate": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${agent_lambda_arn}",
        "Payload": {
          "task": "generate",
          "user_id.$": "$.user_id",
          "job_id.$": "$.job_id",
          "product.$": "$.product",
          "adjustments.$": "$.adjustments",
          "context": {
            "analyze": {
              "output.$": "$.analyze_result.Payload.output"
            },
            "market_insight": {
              "output.$": "$.market_insight_result.Payload.output"
            }
          }
        }
      },
      "ResultPath": "$.generate_result",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "FailState"
        }
      ],
      "TimeoutSeconds": 900,
      "Next": "Optimize"
    },
    "Optimize": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${agent_lambda_arn}",
        "Payload": {
          "task": "optimize",
          "user_id.$": "$.user_id",
          "job_id.$": "$.job_id",
          "product.$": "$.product",
          "adjustments.$": "$.adjustments",
          "context": {
            "analyze": {
              "output.$": "$.analyze_result.Payload.output"
            },
            "market_insight": {
              "output.$": "$.market_insight_result.Payload.output"
            },
            "generate": {
              "output.$": "$.generate_result.Payload.output"
            }
          }
        }
      },
      "ResultPath": "$.optimize_result",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "FailState"
        }
      ],
      "TimeoutSeconds": 900,
      "Next": "Review"
    },
    "Review": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${agent_lambda_arn}",
        "Payload": {
          "task": "review",
          "user_id.$": "$.user_id",
          "job_id.$": "$.job_id",
          "product.$": "$.product",
          "adjustments.$": "$.adjustments",
          "context": {
            "analyze": {
              "output.$": "$.analyze_result.Payload.output"
            },
            "market_insight": {
              "output.$": "$.market_insight_result.Payload.output"
            },
            "generate": {
              "output.$": "$.generate_result.Payload.output"
            },
            "optimize": {
              "output.$": "$.optimize_result.Payload.output"
            }
          }
        }
      },
      "ResultPath": "$.review_result",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "FailState"
        }
      ],
      "TimeoutSeconds": 900,
      "Next": "Prompt"
    },
    "Prompt": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${agent_lambda_arn}",
        "Payload": {
          "task": "prompt",
          "user_id.$": "$.user_id",
          "job_id.$": "$.job_id",
          "hook.$": "$.review_result.Payload.output.final_hook",
          "scenes.$": "$.review_result.Payload.output.final_scenes",
          "call_to_action.$": "$.review_result.Payload.output.final_cta",
          "full_voiceover_text.$": "$.review_result.Payload.output.final_voiceover",
          "product_title.$": "$.product.title",
          "visual_elements.$": "$.analyze_result.Payload.output.visual_elements"
        }
      },
      "ResultPath": "$.prompt_result",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "FailState"
        }
      ],
      "TimeoutSeconds": 900,
      "Next": "TTS"
    },
    "TTS": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${tts_lambda_arn}",
        "Payload": {
          "user_id.$": "$.user_id",
          "job_id.$": "$.job_id",
          "tts_script.$": "$.review_result.Payload.output.final_voiceover",
          "voice_gender": "female"
        }
      },
      "ResultPath": "$.tts_result",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "FailState"
        }
      ],
      "TimeoutSeconds": 900,
      "Next": "Video"
    },
    "Video": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${video_lambda_arn}",
        "Payload": {
          "user_id.$": "$.user_id",
          "job_id.$": "$.job_id",
          "video_prompt.$": "$.prompt_result.Payload.output.master_prompt",
          "audio_s3_key.$": "$.tts_result.Payload.audio_s3_key"
        }
      },
      "ResultPath": "$.video_result",
      "Retry": [
        {
          "ErrorEquals": ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "FailState"
        }
      ],
      "TimeoutSeconds": 900,
      "Next": "Complete"
    },
    "Complete": {
      "Type": "Succeed"
    },
    "FailState": {
      "Type": "Fail",
      "Cause": "An error occurred during video generation pipeline execution",
      "Error": "PipelineExecutionError"
    }
  }
}
