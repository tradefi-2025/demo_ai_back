package org.trader.backdemo.dto.response;

import lombok.Builder;
import lombok.Data;


@Data
@Builder
public class LogInReponse {
    Long userId;
    String name;
    String email;
}
