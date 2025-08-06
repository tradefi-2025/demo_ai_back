package org.trader.backdemo.dto.request;

import lombok.Data;

import java.util.Map;

@Data
public class AgentFormRequest {
    private String username;
    private String agentName;
    private String email;
    private String targetMarket;
    private String inputStartTime;
    private String inputEndTime;
    private String inputFrequency;
    private String outputStartTime;
    private String outputEndTime;
    private String outputFrequency;
    private Map<String, Map<String, String>> features;


}
