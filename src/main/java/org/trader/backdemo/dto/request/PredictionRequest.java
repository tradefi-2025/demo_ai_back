package org.trader.backdemo.dto.request;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.time.LocalDate;

@Data
public class PredictionRequest {
    Long agentId;

    @JsonFormat(pattern = "yyyy-MM-dd")
    LocalDate predictionDate;
}
