package org.trader.backdemo.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import org.trader.backdemo.converter.DoubleArrayConverter;

import java.time.LocalDateTime;

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
    private LocalDateTime predictionDate;

    @Column(name = "predicted_data", columnDefinition = "TEXT")
    @Convert(converter = DoubleArrayConverter.class)
    private double[] predictedData;

    @Column(name = "actual_market", columnDefinition = "TEXT")
    @Convert(converter = DoubleArrayConverter.class)
    private double[] actualMarket;

    @ManyToOne
    @JoinColumn(name = "agent_id")
    @JsonIgnore
    private AgentEntity agent;


}
