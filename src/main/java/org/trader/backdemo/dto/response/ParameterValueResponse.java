package org.trader.backdemo.dto.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ParameterValueResponse {
    private Long id;
    private String name;
    private String value;
    private String defaultValue;
    private String type;
    private boolean required;
}
