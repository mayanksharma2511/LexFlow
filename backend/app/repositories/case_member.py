from sqlalchemy.orm import Session

from app.models.case_member import CaseMember


class CaseMemberRepository:

    def create(
        self,
        db: Session,
        member: CaseMember,
    ) -> CaseMember:
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    def get_by_case(
        self,
        db: Session,
        case_id: str,
    ) -> list[CaseMember]:
        return (
            db.query(CaseMember)
            .filter(CaseMember.case_id == case_id)
            .all()
        )

    def get_by_case_and_user(
        self,
        db: Session,
        case_id: str,
        user_id: str,
    ) -> CaseMember | None:
        return (
            db.query(CaseMember)
            .filter(
                CaseMember.case_id == case_id,
                CaseMember.user_id == user_id,
            )
            .first()
        )


case_member_repository = CaseMemberRepository()
