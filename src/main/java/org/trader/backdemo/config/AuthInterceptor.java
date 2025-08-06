package org.trader.backdemo.config;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class AuthInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request,
                             HttpServletResponse response,
                             Object handler) throws Exception {

        // Si c'est une requête d'auth (/login, /register), on laisse passer
        if (request.getRequestURI().startsWith("/api/auth/")) {
            return true; // Continue vers le contrôleur
        }

        // Pour toutes les autres requêtes, on vérifie la session
        HttpSession session = request.getSession(false); // false = ne pas créer si n'existe pas

        if (session == null || session.getAttribute("user") == null) {
            // Pas de session ou pas d'utilisateur dans la session
            response.setStatus(401);
            response.setContentType("application/json");
            response.getWriter().write("{\"error\":\"Non authentifié\"}");
            return false; // Bloque la requête, n'atteint pas le contrôleur
        }

        return true; // Utilisateur authentifié, laisse passer
    }
}
