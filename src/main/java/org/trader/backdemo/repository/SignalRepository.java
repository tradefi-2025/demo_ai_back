package org.trader.backdemo.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import org.trader.backdemo.entity.SignalEntity;

import java.util.List;
import java.util.Optional;

@Repository
public interface SignalRepository extends JpaRepository<SignalEntity, Long> {

    List<SignalEntity> findByAgentUserIdOrderBySignalDateDesc(Long userId);

    Optional<SignalEntity> findByIdAndAgentUserId(Long id, Long userId);
}
