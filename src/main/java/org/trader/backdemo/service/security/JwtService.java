package org.trader.backdemo.service.security;


import lombok.Data;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseCookie;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Service;
import org.trader.backdemo.entity.UserEntity;

import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;

@Data
@Service
public class JwtService {

    private final String jwtSecret;
    private final Long jwtExpirationMs;
    private final boolean secure;
    private final int maxAgeSeconds;
    private final String COOKIE_NAME = "accessToken";


    public JwtService(
            @Value("${trader.app.security.jwtSecret}") String jwtSecret,
            @Value("${trader.app.security.jwtExpirationMs:86400000}") Long jwtExpirationMs,
            @Value("${trader.app.cookie.secure:false}") boolean secure,
            @Value("${trader.app.cookie.maxAgeSeconds:86399}") int maxAgeSeconds) {
        this.jwtSecret = jwtSecret;
        this.jwtExpirationMs = jwtExpirationMs;
        this.secure = secure;
        this.maxAgeSeconds = maxAgeSeconds;

    }

    private Key getSecretKey() {
        return Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
    }

    public String generateJwtToken(UserEntity userEntity) {
        Date now = new Date();
        Date exp = new Date(now.getTime() + jwtExpirationMs);
        return Jwts.builder()
                .setId(userEntity.getId().toString())
                .setSubject(userEntity.getEmail())
                .setIssuedAt(now)
                .setExpiration(exp)
                .signWith(getSecretKey(), SignatureAlgorithm.HS256)
                .compact();
    }


    public String getUserIdFromJwtToken(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(getSecretKey())
                .build()
                .parseClaimsJws(token)
                .getBody()
                .getId();
    }


    public boolean validateJwtToken(String authToken) {
        try {
            Jwts.parserBuilder().setSigningKey(getSecretKey()).build().parseClaimsJws(authToken);
            return true;
        } catch (SignatureException e) {
            System.err.println("Invalid JWT signature");
        } catch (MalformedJwtException e) {
            System.err.println("Invalid JWT token");
        } catch (ExpiredJwtException e) {
            System.err.println("JWT token is expired");
        } catch (IllegalArgumentException e) {
            System.err.println("JWT claims string is empty");
        }
        return false;
    }

    public ResponseCookie getResponseCookie(UserEntity userEntity) {
        return ResponseCookie.from(COOKIE_NAME, generateJwtToken(userEntity))
                .httpOnly(true)
                .secure(secure)
                .path("/")               // Valide pour tout le site
                .maxAge(maxAgeSeconds)    // 1 jour (en secondes)
                .build();
    }

    public ResponseCookie getCleanJwtCookie() {
        return ResponseCookie.from(COOKIE_NAME, "")
                .path("/")
                .maxAge(0) // Expire immédiatement pour supprimer le cookie
                .build();
    }
}
