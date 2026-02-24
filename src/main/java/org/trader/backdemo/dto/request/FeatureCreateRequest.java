package org.trader.backdemo.dto.request;

import jakarta.validation.constraints.NotBlank;

import java.util.Set;

public record FeatureCreateRequest(
        @NotBlank
        String name,
        String description,
        Set<ParameterDefinitionRequest> parameterDefinitionRequest
) {
}
