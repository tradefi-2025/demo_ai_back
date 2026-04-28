package org.trader.backdemo.dto.request;

import lombok.Data;

import java.util.Map;

@Data
public class AgentFormRequest {
    private String name;
    private String version;
    private Map<String, Map<String, String>> features;
}
