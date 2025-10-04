package org.trader.backdemo.dto.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Set;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AgentFeatureResponse {
    private Long id;
    private Long featureId;
    private String featureName;
    private String featureDescription;
    private Set<ParameterValueResponse> parameters;
}
