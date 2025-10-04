package org.trader.backdemo.entity;


import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Entity
@Getter
@Setter
@Table(name = "parameter_value")

public class ParameterValueEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "parameter_value_id")
    private Long id;

    private String value;

    @ManyToOne
    @JoinColumn(name = "agent_feature_id")
    private AgentFeatureEntity agentFeature;

    @ManyToOne
    @JoinColumn(name = "parameter_definition_id")
    private ParameterDefinitionEntity parameterDefinition;


}
