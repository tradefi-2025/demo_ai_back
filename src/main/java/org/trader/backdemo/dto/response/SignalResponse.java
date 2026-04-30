package org.trader.backdemo.dto.response;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Builder;
import lombok.Data;
import org.trader.backdemo.entity.SignalEntity;

import java.time.LocalDateTime;

@Builder
@Data
public class SignalResponse {
    private long signalId;
    private long agentId;
    private String agentName;
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime signalDate;
    private String estimatedAction;
    private String signal;
    private Double probability;
    private SignalProbabilitiesResponse probabilities;
    private Double volume;
    private Double notional;
    private Double stopLossPrice;
    private Double riskAmount;
    private String sizingMethod;
    private String[] warnings;
    private SignalEntity.SignalStatus status;
}
