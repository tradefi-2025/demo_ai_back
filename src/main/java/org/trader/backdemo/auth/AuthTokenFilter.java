package org.trader.backdemo.auth;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;
import org.trader.backdemo.entity.UserEntity;
import org.trader.backdemo.repository.UserRepository;
import org.trader.backdemo.service.security.AppUserPrincipal;
import org.trader.backdemo.service.security.JwtService;

import java.io.IOException;
import java.util.Optional;

@RequiredArgsConstructor
public class AuthTokenFilter extends OncePerRequestFilter {

    private static final String COOKIE_NAME = "accessToken";
    private final JwtService jwtUtils;
    private final UserRepository userRepository;


    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        try {
            String parsedjwt = resolveToken(request);
            if (parsedjwt != null && jwtUtils.validateJwtToken(parsedjwt)) {
                String userId = jwtUtils.getUserIdFromJwtToken(parsedjwt);
                Optional<UserEntity> userEntity = userRepository.findById(Long.parseLong(userId));
                if (userEntity.isEmpty()) {
                    throw new UsernameNotFoundException("User not found with id: " + userId);
                }

                UserDetails userDetails = AppUserPrincipal.from(userEntity.get());
                UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                        userDetails, null, userDetails.getAuthorities());
                authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

                SecurityContextHolder.getContext().setAuthentication(authentication);
            }
        } catch (Exception e) {
            System.err.println(e.getMessage());
        }

        filterChain.doFilter(request, response);
    }

    private String resolveToken(HttpServletRequest request) {
        String headerAuth = request.getHeader("Authorization");
        if (StringUtils.hasText(headerAuth) && headerAuth.startsWith("Bearer ")) {
            return headerAuth.substring(7);
        }
        Cookie[] cookies = request.getCookies();
        if (cookies != null) {
            for (Cookie c : cookies) {
                if (COOKIE_NAME.equals(c.getName()) && StringUtils.hasText(c.getValue())) {
                    return c.getValue();
                }
            }
        }
        return null;
    }
}
