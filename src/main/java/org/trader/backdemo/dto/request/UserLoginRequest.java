package org.trader.backdemo.dto.request;

import lombok.Data;
import jakarta.validation.constraints

        .NotBlank;
import jakarta.validation.constraints.Email;

@Data
public class UserLoginRequest {

    @NotBlank(message = "L'email est obligatoire")
    @Email(message = "Format d'email invalide")
    String email;

    @NotBlank(message = "Le mot de passe est obligatoire")
    String password;
}
