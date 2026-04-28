package org.trader.backdemo.dto.response;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Builder
@Data
public class PredictionResponse {
    private long predictionId;
    private long agentId;
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime predictionDate;
    private double[] prediction;
    private double[] actualMarket;
}
