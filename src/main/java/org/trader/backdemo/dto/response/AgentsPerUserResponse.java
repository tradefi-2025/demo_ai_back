package org.trader.backdemo.dto.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.trader.backdemo.entity.AgentEntity;

import java.util.Set;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class AgentsPerUserResponse {
    private Long id;
    private String name;
    private String targetMarket;
    private String inputStartTime;
    private String inputEndTime;
    private AgentEntity.Frequency frequency;
    private String outputStartTime;
    private String outputEndTime;
    private AgentEntity.TradingScale tradingScale;
    private String version;
    private AgentEntity.Status trainingStatus;
    private Set<AgentFeatureResponse> agentFeatures;
}