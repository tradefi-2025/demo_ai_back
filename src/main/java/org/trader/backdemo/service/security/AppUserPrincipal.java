package org.trader.backdemo.service.security;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.trader.backdemo.entity.UserEntity;

import java.util.Collection;
import java.util.List;

public class AppUserPrincipal implements UserDetails {

    private final Long id;
    private final String username;
    private final String password;
    private final Collection<? extends GrantedAuthority> authorities;
    private final boolean enabled;
    private final boolean accountNonExpired;
    private final boolean credentialsNonExpired;
    private final boolean accountNonLocked;

    public AppUserPrincipal(Long id,
                            String username,
                            String password,
                            Collection<? extends GrantedAuthority> authorities,
                            boolean enabled,
                            boolean accountNonExpired,
                            boolean credentialsNonExpired,
                            boolean accountNonLocked) {
        this.id = id;
        this.username = username;
        this.password = password;
        this.authorities = authorities != null ? authorities : List.of();
        this.enabled = enabled;
        this.accountNonExpired = accountNonExpired;
        this.credentialsNonExpired = credentialsNonExpired;
        this.accountNonLocked = accountNonLocked;
    }

    public Long getId() {
        return id;
    }

    public static AppUserPrincipal from(UserEntity user) {
        String login = user.getEmail();
        return new AppUserPrincipal(
                user.getId(),
                login,
                user.getPassword(),
                List.of(), // mappez vos rôles en GrantedAuthority si nécessaire
                true,
                true,
                true,
                true
        );
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    @Override
    public String getPassword() {
        return password;
    }

    @Override
    public String getUsername() {
        return username;
    }

    @Override
    public boolean isAccountNonExpired() {
        return accountNonExpired;
    }

    @Override
    public boolean isAccountNonLocked() {
        return accountNonLocked;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return credentialsNonExpired;
    }

    @Override
    public boolean isEnabled() {
        return enabled;
    }
}