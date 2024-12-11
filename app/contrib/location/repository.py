from typing import TYPE_CHECKING, Optional
from sqlalchemy import update
from app.db.repository import CRUDBaseSync, prepare_data_with_slug_sync

from .models import Place, PlaceTranslation

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class CRUDPlaceSync(CRUDBaseSync[Place]):
    def create_with_translation(
            self,
            db: "Session",
            obj_in: dict,
            lang: str,
    ):
        name = obj_in.get("name")
        prepared = prepare_data_with_slug_sync(
            db=db,
            obj_in={"slug": obj_in.get('slug'), "name": name},
            obj_repo_sync=self,
            from_field="name",
        )

        try:
            db_obj = self.model(
                slug=prepared.get("slug"),
                parent_id=obj_in.get("parent_id"),
                location_level=obj_in.get("location_level"),
                is_active=obj_in.get("is_active")
            )

            db.add(db_obj)
            db.flush()

            db_obj_tr = PlaceTranslation(
                id=db_obj.id,
                name=name,
                full_name=obj_in.get('full_name'),
                locale=lang,
            )
            db.add(db_obj_tr)
            db.commit()
            db.refresh(db_obj)
            db.refresh(db_obj_tr)
            db_obj.current_translation = db_obj_tr
            return db_obj
        except Exception as e:
            print(e)
            db.rollback()
            raise e

    # def update(
    #         self,
    #         db: "Session",
    #         *,
    #         db_obj: Place,
    #         obj_in: dict,
    #         commit: Optional[bool] = True
    # ) -> Place:
    #     # obj_data = jsonable_encoder(db_obj, custom_encoder={Choices: lambda x: x.value})
    #     # if isinstance(obj_in, dict):
    #     #     update_data = obj_in
    #     # else:
    #     #     update_data = obj_in.model_dump(exclude_unset=True)
    #
    #     # for field in obj_data:
    #     #     if field in update_data:
    #     #         setattr(db_obj, field, update_data[field])
    #     # new_db_obj = Place(
    #     #     id=db_obj.id,
    #     #     **obj_in,
    #     #     # slug=obj_in.get('slug'),
    #     #     # is_active=obj_in.get('is_active'),
    #     #     # parent_id=obj_in.get('parent_id'),
    #     #     # location_level=obj_in.get('location_level'),
    #     # )
    #     # db.add(new_db_obj)
    #     if commit:
    #         db.commit()
    #         # db.refresh(new_db_obj)
    #     return db_obj


class CRUDPlaceTranslationSync(CRUDBaseSync[PlaceTranslation]):
    pass


place_repo_sync = CRUDPlaceSync(Place)
place_tr_repo_sync = CRUDPlaceTranslationSync(PlaceTranslation)
