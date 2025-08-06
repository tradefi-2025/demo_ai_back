package org.trader.backdemo.dto.session;

import lombok.Builder;
import lombok.Data;

import java.io.Serializable;

@Builder
@Data

public class SessionUser implements Serializable {
    private static final long serialVersionUID = 1L;

    private Long userId;
    private String email;
    private String name;
}
