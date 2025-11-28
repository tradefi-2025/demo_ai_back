package org.trader.backdemo.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import org.trader.backdemo.converter.DoubleArrayConverter;

import java.time.LocalDate;

@Entity
@Getter
@Setter
@Table(name = "prediction")
public class PredictionEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "prediction_id")
    private long id;

    @Column(name = "prediction_date")
    private LocalDate predictionDate;

    @Column(name = "predicted_data", columnDefinition = "TEXT")
    @Convert(converter = DoubleArrayConverter.class)
    private double[][] predictedData;

    @ManyToOne
    @JoinColumn(name = "agent_id")
    @JsonIgnore
    private AgentEntity agent;


}
