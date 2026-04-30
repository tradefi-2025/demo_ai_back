package org.trader.backdemo.dto.request;

import lombok.Data;
import org.trader.backdemo.entity.SignalEntity;

@Data
public class SignalStatusUpdateRequest {
    private SignalEntity.SignalStatus status;
}
