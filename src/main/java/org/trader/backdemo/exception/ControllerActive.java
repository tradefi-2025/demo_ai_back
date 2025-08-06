package org.trader.backdemo.exception;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.trader.backdemo.exception.domaine.ExistingUserException;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * Contrôleur actif qui intercepte les exceptions avant qu'elles n'atteignent Spring Security
 * pour fournir des réponses d'erreur personnalisées et cohérentes.
 */
@RestControllerAdvice
public class ControllerActive {


    /**
     * Gère les exceptions d'authentification (informations d'identification incorrectes, etc.)
     */
    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<Map<String, Object>> handleAuthenticationException(AuthenticationException ex, HttpServletRequest request) {

        Map<String, Object> errorDetails = new HashMap<>();
        errorDetails.put("timestamp", LocalDateTime.now().toString());
        errorDetails.put("status", HttpStatus.UNAUTHORIZED.value());
        errorDetails.put("message", "Échec de l'authentification: " + ex.getMessage());
        errorDetails.put("path", request.getRequestURI());

        return new ResponseEntity<>(errorDetails, HttpStatus.UNAUTHORIZED);
    }

    /**
     * Gère les exceptions spécifiques aux identifiants incorrects
     */
    @ExceptionHandler(BadCredentialsException.class)
    public ResponseEntity<Map<String, Object>> handleBadCredentialsException(BadCredentialsException ex, HttpServletRequest request) {

        Map<String, Object> errorDetails = new HashMap<>();
        errorDetails.put("timestamp", LocalDateTime.now().toString());
        errorDetails.put("status", HttpStatus.UNAUTHORIZED.value());
        errorDetails.put("message", "Identifiants incorrects");
        errorDetails.put("path", request.getRequestURI());

        return new ResponseEntity<>(errorDetails, HttpStatus.UNAUTHORIZED);
    }

    /**
     * Gère les exceptions d'accès refusé
     */
    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<Map<String, Object>> handleAccessDeniedException(AccessDeniedException ex, HttpServletRequest request) {

        Map<String, Object> errorDetails = new HashMap<>();
        errorDetails.put("timestamp", LocalDateTime.now().toString());
        errorDetails.put("status", HttpStatus.FORBIDDEN.value());
        errorDetails.put("message", "Accès refusé: " + ex.getMessage());
        errorDetails.put("path", request.getRequestURI());

        return new ResponseEntity<>(errorDetails, HttpStatus.FORBIDDEN);
    }

    /**
     * Gère l'exception pour utilisateur existant
     */
    @ExceptionHandler(ExistingUserException.class)
    public ResponseEntity<Map<String, Object>> handleExistingUserException(ExistingUserException ex, HttpServletRequest request) {

        Map<String, Object> errorDetails = new HashMap<>();
        errorDetails.put("timestamp", LocalDateTime.now().toString());
        errorDetails.put("status", HttpStatus.CONFLICT.value());
        errorDetails.put("message", ex.getMessage());
        errorDetails.put("path", request.getRequestURI());

        return new ResponseEntity<>(errorDetails, HttpStatus.CONFLICT);
    }

    /**
     * Gère toutes les autres exceptions non spécifiquement traitées
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGenericException(Exception ex, HttpServletRequest request) {

        Map<String, Object> errorDetails = new HashMap<>();
        errorDetails.put("timestamp", LocalDateTime.now().toString());
        errorDetails.put("status", HttpStatus.INTERNAL_SERVER_ERROR.value());
        errorDetails.put("message", "Une erreur inattendue s'est produite");
        errorDetails.put("path", request.getRequestURI());

        return new ResponseEntity<>(errorDetails, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}
