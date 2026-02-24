package org.trader.backdemo.dto.request;

import jakarta.validation.constraints.NotBlank;

public record ParameterDefinitionRequest(
        @NotBlank
        String name,
        String defaultValue,
        String type,
        String description,
        boolean required) {
}
