# Security Policy

## Reporting Security Vulnerabilities

**Do not open public issues for security vulnerabilities.**

If you discover a security vulnerability, please email us at **security@drcsystems.com** with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any proof-of-concept code

We will acknowledge receipt within 24 hours and provide an update within 72 hours.

## Security Practices

### Portal Security

1. **Row-Level Access Control**
   - Users can only see their own records
   - Strict domain filtering on all database queries
   - Validated at both backend and frontend

2. **CSRF Protection**
   - All AJAX calls include CSRF tokens
   - Tokens validated on every POST/PUT/DELETE request
   - Tokens refreshed on sensitive operations

3. **Input Validation**
   - All user input validated on backend
   - Client-side validation for UX only
   - Sanitization of all user-provided data

4. **Output Encoding**
   - HTML escaped in all templates
   - JavaScript strings properly quoted
   - Special characters encoded in URLs

### Data Protection

1. **Field-Level Security**
   - Sensitive fields protected by ir.rule
   - Personal data handled with care
   - Audit trail maintained for sensitive changes

2. **Authentication**
   - Relies on Odoo's built-in authentication
   - Portal group membership required
   - Session tokens validated per request

3. **Authorization**
   - Record rules enforce data isolation
   - Group-based permissions
   - Method-level access control

## Secure Coding Guidelines

### Python Backend

```python
# ✅ Good: Validate input and use domain filters
def get_employee_leaves(self, employee_id):
    employee = request.env.user.employee_id
    if employee.id != int(employee_id):
        raise AccessError('Access Denied')
    
    return request.env['hr.leave'].search([
        ('employee_id', '=', employee.id),
        ('state', 'in', ['draft', 'confirm'])
    ])

# ❌ Bad: No validation, raw SQL
leaves = request.env.execute(
    f"SELECT * FROM hr_leave WHERE id = {leave_id}"
)
```

### JavaScript Frontend

```javascript
// ✅ Good: Escape and validate
window.deleteEntry = function(id) {
    if (!confirm('Delete this entry?')) return;
    
    fetch('/endpoint', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('[name="csrf_token"]').value
        },
        body: JSON.stringify({id: parseInt(id)})
    });
};

// ❌ Bad: No CSRF token, no validation
window.deleteEntry = function(id) {
    fetch(`/endpoint?id=${id}`, {method: 'POST'});
};
```

### XML Templates

```xml
<!-- ✅ Good: Proper escaping -->
<t t-esc="user.name"/>
<t t-att-onclick="'deleteEntry(&quot;%d&quot;)' % entry.id"/>

<!-- ❌ Bad: Direct output, no escaping -->
<span t-out="user.name"/>
<a t-att-onclick="deleteEntry('%s')" t-att-data-id="entry.id"/>
```

## Security Testing

### Manual Security Audit Checklist

- [ ] Try accessing other employees' leave records (should fail)
- [ ] Try modifying URLs to access other users' timesheets (should fail)
- [ ] Check CSRF tokens are present in AJAX requests
- [ ] Verify all inputs are validated on backend
- [ ] Test with SQL injection attempts (should sanitize)
- [ ] Test with XSS payloads in text fields (should encode)
- [ ] Verify session timeout works
- [ ] Check logs for suspicious activity

### Automated Testing

Run security checks:
```bash
# Python linting
flake8 hr_ess_portal/ --select=S

# Check for common vulnerabilities
bandit -r hr_ess_portal/
```

## Dependency Security

### Keeping Dependencies Updated

- Monitor security advisories for Odoo
- Update Python dependencies regularly
- Pin versions in production
- Test updates in staging before production

### Vulnerability Disclosure

When a vulnerability is discovered:
1. Assess severity (Critical, High, Medium, Low)
2. Develop a fix on a private branch
3. Test the fix thoroughly
4. Release as a patch version
5. Update SECURITY.md with CVE info

## Compliance

This module respects:
- GDPR data protection requirements
- LGPL-3 license terms
- Odoo security best practices
- Enterprise security standards

## Security Resources

- [Odoo Security Guidelines](https://www.odoo.com/documentation/19.0/developer/howtos/security.html)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://owasp.org/www-community/attacks/Code_Injection)
- [JavaScript Security](https://owasp.org/www-project-web-security-testing-guide/)

## Incident Response

If a security incident occurs:
1. Stop all affected systems
2. Assess the impact
3. Notify affected users
4. Develop and test a fix
5. Release a patched version
6. Post-mortem analysis

## Support

- Report vulnerabilities: **security@drcsystems.com**
- Security questions: [GitHub Discussions](https://github.com/meet1432/hr-ess-portal/discussions)
- File issues: [GitHub Issues](https://github.com/meet1432/hr-ess-portal/issues)

---

**Last Updated**: July 2024

Thank you for helping keep this project secure! 🔐