package org.trader.backdemo.dto.request;

import lombok.Data;

@Data

public class UserInscriptionRequest {
    String email;
    String name;
    String password;
}
