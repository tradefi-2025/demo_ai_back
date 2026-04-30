package org.trader.backdemo.dto.response;

import lombok.Builder;
import lombok.Data;

@Builder
@Data
public class SignalProbabilitiesResponse {
    private Double sell;
    private Double hold;
    private Double buy;
}
