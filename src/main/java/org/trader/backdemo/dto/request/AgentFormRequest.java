package org.trader.backdemo.dto.request;

import lombok.Data;
import org.trader.backdemo.entity.AgentEntity;

import java.util.Map;

@Data
public class AgentFormRequest {
    private String name;
    private String targetMarket;
    private String inputStartTime;
    private String inputEndTime;
    private AgentEntity.Frequency frequency;
    private String outputStartTime;
    private String outputEndTime;
    private AgentEntity.TradingScale tradingScale;
    private String version;
    private Map<String, Map<String, String>> features;
}
