package org.trader.backdemo.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import org.trader.backdemo.dto.response.ParameterDefinitionResponse;

import java.util.Map;
@Data

public class Feature {
    @JsonProperty("name")
    String name;
    @JsonProperty("description")
    String description;
    @JsonProperty("parameters")
    Map<String, ParameterDefinitionResponse> parameters;
}
