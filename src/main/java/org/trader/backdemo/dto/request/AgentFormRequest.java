package org.trader.backdemo.dto.request;

import lombok.Data;

import java.util.Map;

@Data
public class AgentFormRequest {
    private String name;
    private String targetMarket;
    private String inputStartTime;
    private String inputEndTime;
    private int inputFrequency;
    private String outputStartTime;
    private String outputEndTime;
    private int outputFrequency;
    private Map<String, Map<String, String>> features;
}
