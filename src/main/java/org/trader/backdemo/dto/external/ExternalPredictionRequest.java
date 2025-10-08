package org.trader.backdemo.dto.external;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ExternalPredictionRequest {
    private Long agentId;

    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate predictionDate;
}
