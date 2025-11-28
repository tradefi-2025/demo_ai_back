package org.trader.backdemo.entity;

import com.fasterxml.jackson.annotation.JsonBackReference;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonManagedReference;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.util.HashSet;
import java.util.Set;

@Entity
@Getter
@Setter
@Table(name = "agent_feature")
public class AgentFeatureEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "agent_feature_id")
    @JsonIgnore
    private Long id;

    @ManyToOne
    @JoinColumn(name = "agent_id")
    @JsonBackReference
    private AgentEntity agent;

    @ManyToOne
    @JoinColumn(name = "feature_id")
    @JsonManagedReference
    private FeatureEntity feature;

    @OneToMany(mappedBy = "agentFeature", cascade = CascadeType.ALL, orphanRemoval = true)
    private Set<ParameterValueEntity> parameterValues = new HashSet<>();
}