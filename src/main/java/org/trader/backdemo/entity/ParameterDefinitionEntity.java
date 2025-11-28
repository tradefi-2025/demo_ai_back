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
@Setter
@Getter
@Table(name = "parameter_definition")

public class ParameterDefinitionEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "parameter_definition_id")
    @JsonIgnore
    private Long id;

    private String name;

    private String defaultValue;

    @Enumerated(EnumType.STRING)
    private parameterTypeEnum type;

    private boolean required;
    @OneToMany(mappedBy = "parameterDefinition", cascade = CascadeType.ALL, orphanRemoval = true)
    @JsonManagedReference
    private Set<ParameterValueEntity> parameterValues = new HashSet<>();

    @ManyToOne
    @JsonBackReference
    @JoinColumn(name = "feature_id")
    private FeatureEntity feature;

    public enum parameterTypeEnum {
        INTEGER,
        DOUBLE,
        STRING,
        BOOLEAN,
        DATE
    }


}
