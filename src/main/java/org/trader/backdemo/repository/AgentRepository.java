package org.trader.backdemo.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import org.trader.backdemo.entity.AgentEntity;



@Repository
public interface AgentRepository extends JpaRepository<AgentEntity, Long> {


}
