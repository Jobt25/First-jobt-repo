from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'phone_number', 'first_name', 'last_name', 
                   'is_staff', 'is_active', 'id_verified', 'verification_lev')
    list_filter = ('is_staff', 'is_active', 'verification_lev', 'id_verified')
    list_editable = ('is_active', 'verification_lev')  # Allows quick editing from list view
    
    fieldsets = (
        (None, {'fields': ('email', 'phone_number', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'date_of_birth')}),
        ('Verification', {
            'fields': ('id_type', 'id_number', 'id_verified', 'verification_lev'),
            'classes': ('collapse',)  # Makes this section collapsible
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 
                      'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'phone_number', 
                'first_name', 'last_name', 
                'password1', 'password2',
                'is_active', 'is_staff'
            )
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name', 'phone_number', 'id_number')
    ordering = ('-created_at',)  # Newest users first
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    filter_horizontal = ('groups', 'user_permissions',)  # Better widget for many-to-many
    
    actions = ['verify_users', 'unverify_users', 'activate_users', 'deactivate_users']
    
    def verify_users(self, request, queryset):
        updated = queryset.update(id_verified=True, verification_lev=2)
        self.message_user(request, f'{updated} users verified successfully')
    verify_users.short_description = "Verify selected users"
    
    def unverify_users(self, request, queryset):
        updated = queryset.update(id_verified=False, verification_lev=0)
        self.message_user(request, f'{updated} users unverified')
    unverify_users.short_description = "Unverify selected users"
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated')
    deactivate_users.short_description = "Deactivate selected users"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'website', 'profile_picture_preview')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'website')
    list_select_related = ('user',)
    raw_id_fields = ('user',)  # Better for large user databases
    
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            from django.utils.html import format_html
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius:50%;" />',
                obj.profile_picture.url
            )
        return "-"
    profile_picture_preview.short_description = 'Profile Picture'

# Register User model after all configurations
admin.site.register(User, CustomUserAdmin)