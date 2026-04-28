package org.trader.backdemo.dto.response;

import lombok.Data;

import java.util.List;

@Data
public class ParameterDefinitionResponse {
    private String name;
    private String defaultValue;
    private String description;
    private String minValue;
    private String maxValue;
    private String type;
    private List<String> enumValues;
    private String fileName;
    private boolean required;
}
