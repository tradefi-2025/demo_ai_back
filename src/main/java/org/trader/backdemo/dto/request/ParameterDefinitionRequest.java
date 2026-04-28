package org.trader.backdemo.dto.request;

import com.fasterxml.jackson.annotation.JsonAlias;
import jakarta.validation.constraints.NotBlank;

import java.util.List;

public record ParameterDefinitionRequest(
        @NotBlank
        String name,
        String defaultValue,
        String type,
        String description,
        @JsonAlias("min")
        String minValue,
        @JsonAlias("max")
        String maxValue,
        List<String> enumValues,
        String fileName,
        boolean required) {
}
