package org.trader.backdemo.entity;


import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonManagedReference;
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
    @JsonIgnore
    private Long id;

    private String value;

    @ManyToOne
    @JoinColumn(name = "agent_feature_id")
    @JsonIgnore
    private AgentFeatureEntity agentFeature;

    @ManyToOne
    @JoinColumn(name = "parameter_definition_id")
    @JsonManagedReference
    private ParameterDefinitionEntity parameterDefinition;


}
