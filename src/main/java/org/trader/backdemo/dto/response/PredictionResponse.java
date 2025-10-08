package org.trader.backdemo.dto.response;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDate;

@Builder
@Data
public class PredictionResponse {
    private long predictionId;
    private long agentId;
    private String targetMarket;
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate predictionDate;
    private double[][] prediction;
}
